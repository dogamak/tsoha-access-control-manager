import UserLink from '../components/UserLink.vue';
import UserSelector from '../components/UserSelector.vue';
import PhotoUpload from '../components/PhotoUpload.vue';
import InlineGroupList from '../components/InlineGroupList.vue';
import InlineGroupSelector from '../components/InlineGroupSelector.vue';
import AvatarProperty from '../components/AvatarProperty.vue';

export const SELF_EDITABLE = 'self';

export const SUPERVISOR_EDITABLE = 'supervisor';

export const GROUP_EDITABLE = 'group';

export const UserFields = {
    PHOTO: 'UserFields.PHOTO',
    USERNAME: 'UserFields.USERNAME',
    EMAIL: 'UserFields.EMAIL',
    ROLE: 'UserFields.ROLE',
    SUPERVISOR: 'UserFields.SUPERVISOR',
    GROUPS: 'UserFields.GROUPS',
};

export const UserModel = {
    [UserFields.PHOTO]: {
        key: 'avatar',
        label: 'Photo',
        required: false,
        description: 'Avatar photo for the user.',
        editable: SELF_EDITABLE,
        component: AvatarProperty,
        editor: PhotoUpload,
    },

    [UserFields.USERNAME]: {
        key: 'username',
        label: 'Username',
        description: 'Account name used when authenticating.',
        required: true,
        editable: SELF_EDITABLE,
        validator (value) {
            if (!/^[A-Za-z][A-Za-z0-9_.-]+$/.test(value)) {
                return "Username must start with a letter and only contain the characters A-Z, a-z, 0-9 and the symbols ., _ and -.";
            }
        },
    },

    [UserFields.NAME]: {
        key: 'name',
        label: 'Name',
        description: 'Real name of the user',
        required: true,
        editable: SELF_EDITABLE,
        validator: (value) => {
            if (typeof value !== 'string') {
                return "Name must be a string";
            }
        },
    },

    [UserFields.EMAIL]: {
        key: 'email',
        label: 'Email',
        description: 'Primary email address used to contact the user.',
        required: false,
        editable: SELF_EDITABLE,
        validator (value) {
            if (!/^[^@]+@[^@]+$/.test(value)) {
                return "Invalid email address. (Must contain one @-character)";
            }
        },
    },
    
    [UserFields.ROLE]: {
        key: 'role',
        label: 'Role',
        description: 'Role, tile, or position of this user in the organization.',
        required: false,
        editable: SUPERVISOR_EDITABLE,
        validator (value) {
            if (typeof value !== "string") {
                return "Role must be a string.";
            }
        },
    },

    [UserFields.SUPERVISOR]: {
        key: 'supervisor',
        label: 'Supervisor',
        description: 'Supervisor of this user, to whom they report to.',
        required: false,
        editable: SUPERVISOR_EDITABLE,
        editor: UserSelector,
        component: UserLink,
        validator (user) {
            if (typeof user !== "object" || typeof user.id !== "number") {
                return "Invalid value of the supervisor property.";
            }
        },
    },

    [UserFields.GROUPS]: {
        key: 'groups',
        label: 'Groups',
        description: 'Groups member of which this user is.',
        required: false,
        editable: GROUP_EDITABLE,
        component: InlineGroupList,
        editor: InlineGroupSelector,
    },
};

export const group_permissions = [
    {
        key: 'create_users',
        label: 'Create users',
    },
    {
        key: 'edit_users',
        label: 'Edit user details',
    },
    {
        key: 'manage_memberships',
        label: 'Manage group memberships',
    },
];

export const GroupPermissions = group_permissions;